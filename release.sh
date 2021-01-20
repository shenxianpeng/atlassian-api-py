#!/bin/bash

_check_result()
{
    if [ $? -ne 0 ]; then
        exit 1
    else
        echo "[√] last command was successfully executed."
    fi
}

bump_version()
{
  echo "bump version to ?"
  read -r new_version
  sed -i "s/$old_revision/$new_revision/g" setup.py
  _check_result
  echo "[√] bump version successful, new version is:"
  grep "version" setup.py
  _check_result
}

git_push()
{
  current_branch=`git branch --show-current`
  if [ ${current_branch} = "master" ]; then
    git add setup.py
    git commit -m "Bump version to $new_revision"
    git push origin master
    git tag $version
    git push --tag
  else
    echo "[X] Please switch to master branch first."
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
  _check_result
  echo "[√] upload to PyPI successful."
}

echo "Checking release environment"
which python > /dev/null 2>&1
_check_result
which twine > /dev/null 2>&1
_check_result
echo

while true; do
  echo "1. Do you need to upgrade version ?"
  read -r yn
  case $yn in
    [Yy]* ) bump_version ; break ;;
    [Nn]* ) echo; echo "[*] skip upgrade version"; echo; break;;
    * ) echo "Please input yes or no";;
  esac
done

while true; do
  echo "2. Ready to push version changes to GitHub ?"
  read -r yn
  case $yn in
    [Yy]* ) git_push ; break ;;
    [Nn]* ) echo; echo "[*] skip push to Git"; echo; break;;
    * ) echo "Please input yes or no";;
  esac
done

while true; do
  echo "3. Ready to release to PyPI ?"
  read -r yn
  case $yn in
    [Yy]* ) release_to_PyPI ; break ;;
    [Nn]* ) echo; echo "[*] skip deploy to PyPI for release"; echo; break;;
    * ) echo "Please input yes or no";;
  esac
done
