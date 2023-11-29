# Contribution Guide

We would love for you to contribute to the neurodamus project and help make it better than it is today.
As a contributor, here are the guidelines we would like you to follow:

 - [Question or Problem?](#got-a-question)
 - [Issues and Bugs](#found-a-bug)
 - [Feature Requests](#missing-a-feature)
 - [Submissions](#submission-guidelines)
 - [Development Guidelines](#development)
 - [Release Procedure](#release)

# Got a Question?

Please do not hesitate to raise an issue on [github project page][github].

# Found a Bug?

If you find a bug in the source code, you can help us by [submitting an issue](#issues)
to our [GitHub Repository][github]. Even better, you can [submit a Pull Request](#pull-requests) with a fix.

#  Missing a Feature?

You can *request* a new feature by [submitting an issue](#issues) to our GitHub Repository.
If you would like to *implement* a new feature, please submit an issue with a proposal for your
work first, to be sure that we can use it.

Please consider what kind of change it is:

* For a **Major Feature**, first open an issue and outline your proposal so that it can be
discussed. This will also allow us to better coordinate our efforts, prevent duplication of work,
and help you to craft the change so that it is successfully accepted into the project.
* **Small Features** can be crafted and directly [submitted as a Pull Request](#pull-requests).

# Submission Guidelines

## Issues

Before you submit an issue, please search the issue tracker, maybe an issue for your problem
already exists and the discussion might inform you of workarounds readily available.

We want to fix all the issues as soon as possible, but before fixing a bug we need to reproduce
and confirm it. In order to reproduce bugs we will need as much information as possible, and
preferably with an example.

## Pull Requests

When you wish to contribute to the code base, please consider the following guidelines:

* Make a [fork](https://guides.github.com/activities/forking/) of this repository.
* Make your changes in your fork, in a new git branch:

     ```shell
     git checkout -b my-fix-branch master
     ```
* Create your patch, **including appropriate Python test cases**.
  Please check the coding [conventions](#coding-conventions) for more information.
* Run the full test suite, and ensure that all tests pass.
* Commit your changes using a descriptive commit message.

     ```shell
     git commit -a
     ```
* Push your branch to GitHub:

    ```shell
    git push origin my-fix-branch
    ```
* In GitHub, send a Pull Request to the `master` branch of the upstream repository of the relevant component.
* If we suggest changes then:
  * Make the required updates.
  * Re-run the test suites to ensure tests are still passing.
  * Rebase your branch and force push to your GitHub repository (this will update your Pull Request):

       ```shell
        git rebase master -i
        git push -f
       ```

That’s it! Thank you for your contribution!

### After your pull request is merged

After your pull request is merged, you can safely delete your branch and pull the changes from
the main (upstream) repository:

* Delete the remote branch on GitHub either through the GitHub web UI or your local shell as follows:

    ```shell
    git push origin --delete my-fix-branch
    ```
* Check out the master branch:

    ```shell
    git checkout master -f
    ```
* Delete the local branch:

    ```shell
    git branch -D my-fix-branch
    ```
* Update your master with the latest upstream version:

    ```shell
    git pull --ff upstream master
    ```

[github]: https://github.com/BlueBrain/neurodamus

# Development Environment

Please make sure to install the project requirements,
see the [dependencies](./README.md#dependencies) section in top README.

This section applies to both Python versions 2 and 3.

## Setup

It is recommended to use `virtualenv` to develop in a sandbox environment:

```sh
virtualenv venv
. venv/bin/activate

# Install neurodamus in development mode
pip install -e .

# Install test requirements
pip install -r tests/requirements.txt
```

## Testing

There are several test groups in Neurodamus, from plain unit tests to integration and system tests.

While developing you may want to run unit tests very frequently and thus we suggest running the base
tests using pytest directly from the dev environment.
```sh
pytest tests/unit
```

For the next stage testing we suggest using the provided tox environments

```sh
# Integration tests
tox -e integration
```

System and scientific tests require Blue Brain models. They therefore depend on neurodamus-neocortex
`special` builds and should be launched as follows:

```sh
module load unstable neurodamus-neocortex py-neurodamus
# Integration-e2e tests
tox -e bbp-model -- tests/integration-e2e

# Scientific tests
tox -e bbp-model -- tests/scientific
```

### Adding more tests

We kindly ask contributors to add tests alongside their new features or enhancements. With the
previous setup in mind, consider adding test to one or more groups:

 - `tests/unit`: For unit tests of functions with little dependencies. Tests get a few shared mocks,
namely for NEURON and MPI.
 - `tests/integration`: For integration tests. Please place here tests around a component which
   might depend on a number of functions. Tests here can rely on NEURON and the other base
   dependencies. Additionally tests are provided a `special` with synapse mechanisms so that
   Neurodamus can be fully initialized.
 - `tests/integration-e2e`: Place tests here that require launching a top-level Neurodamus instance.
   Examples of it might be testing modes of operation, parameter handling, or simply larger
   integration tests which are validated according to the results.
 - `tests/scientific[-ngv]`: Should contain tests which validate essential scientific features
   implemented in Neurodamus, namely creation of synapses, replay, NGV, neurodamulation, etc.

## Coding conventions

The code coverage of the Python unit-tests may not decrease over time.
It means that every change must go with their corresponding Python unit-tests to
validate the library behavior as well as to demonstrate the API usage.
