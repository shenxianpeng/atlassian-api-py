# Contribution Guidelines

Thank you for your interest in contributing to this project! Please follow these guidelines to ensure a smooth contribution process.

## How to Contribute

1. **Fork the Repository**: Create a personal copy of the repository by forking it on GitHub.

2. **Create a Branch**: Before making changes, create a new branch for your feature or bug fix:
   ```
   git checkout -b my-feature-branch
   ```

3. **Make Changes**: Implement your changes in the new branch.

4. **Write Tests**: Ensure that your changes are covered by tests. If you're adding a new feature, include tests that verify its behavior.

5. **Run Tests**: Before submitting your changes, run the tests to ensure everything is working correctly:
   ```bash
   python3 -m venv .env
   source .env/bin/activate
   pip install nox
   nox -l # see all available sessions
   ```

6. **Commit Your Changes**: Commit your changes with a descriptive commit message:
   ```
   git commit -m "Add my new feature"
   ```

7. **Push to GitHub**: Push your changes to your forked repository:
   ```
   git push origin my-feature-branch
   ```

8. **Create a Pull Request**: Go to the original repository and create a pull request from your branch. Provide a clear description of your changes and why they are needed.

## Reporting Issues

If you encounter any issues or bugs, please report them by creating a new issue in the GitHub repository. Include as much detail as possible, including steps to reproduce the issue and any relevant error messages.

## Questions

If you have any questions or need assistance, feel free to reach out to the project maintainers or ask for help in the community.

Thank you for contributing to this project!
