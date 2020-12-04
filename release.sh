#!/bin/bash

check_exec_result()
{
  if [ $? -ne 0 ]; then
    echo "[X] last execution failed."
    exit 1;
  else
    echo "[√] last execution successful."
  fi
}

bump_version()
{
  read -p "   atlassian-api-py current version is ? " old_version
  read -p "   atlassian-api-py increase version to ? " new_version
  old_revision=`echo $old_version | cut -d. -f3`
  new_revision=`echo $new_version | cut -d. -f3`
  sed -i "s/$old_revision/$new_revision/g" setup.py
  check_result
  echo "[√] completed bump version. new version is:"
  grep "version" setup.py
  check_exec_result
}

git_push()
{
  current_branch=`git branch --show-current`
  if [ ${current_branch} = "master" ]; then
    git add setup.py
    git commit -m "Bump atlassian-api-py version to $new_revision"
    git push origin master
    git tag $version
    git push --tag
  else
    echo "[X] please switch to master branch first."
    exit
  fi
}

release_to_PyPI()
{
  rm -rf dist build > /dev/null 2>&1
  echo "[√] completed clean disk, build folders"
  python setup.py bdist_wheel # add sdist if need
  echo "[√] completed create wheel file"
  twine upload dist/*
  check_exec_result
  echo "[√] upload to PyPI successful."
}

echo "Checking release environment"
which python > /dev/null 2>&1
check_exec_result
which twine > /dev/null 2>&1
check_exec_result
echo

while true; do
  read -p "1. Do you need to upgrade version ? " yn
  case $yn in
    [Yy]* ) bump_version ; break ;;
    [Nn]* ) echo; echo "[*] skip upgrade version"; echo; break;;
    * ) echo "Please input yes or no";;
  esac
done

while true; do
  read -p "2. Ready to push version changes to GitHub ? " yn
  case $yn in
    [Yy]* ) git_push ; break ;;
    [Nn]* ) echo; echo "[*] skip push to Git"; echo; break;;
    * ) echo "Please input yes or no";;
  esac
done

while true; do
  read -p "3. Ready to release to PyPI ? " yn
  case $yn in
    [Yy]* ) release_to_PyPI ; break ;;
    [Nn]* ) echo; echo "[*] skip deploy to PyPI for release"; echo; break;;
    * ) echo "Please input yes or no";;
  esac
done
