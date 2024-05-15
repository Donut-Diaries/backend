#!/usr/bin/bash

###########################
#### RUN TESTS IN VENV ####
###########################

######### Colors ##########
YELLOW() {
    printf "\e[33m"
    "$@"
    printf "\e[0m"
}

GREEN() {
    printf "\e[32m"
    "$@"
    printf "\e[0m"
}

BLUE() {
    printf "\e[34m"
    "$@"
    printf "\e[0m"
}

######## End Colors #########

# Whether to install dependencies
INSTALL_DEPENDENCIES=0

activate_venv() {
    # Activates the python venv if none is activated.

    echo "Activating venv"

    local python_exec
    local sub

    python_exec="$(which python)"
    sub=".cache/pypoetry/virtualenvs"

    if grep -q "$sub" <<<"$python_exec"; then
        BLUE echo -e "Using current poetry shell\n"
    else
        if [[ ! $(poetry env info --path 2>/dev/null) ]]; then
            poetry env use 3.12

            # Install dependencies in new environment
            INSTALL_DEPENDENCIES=1
        fi

        location="$(poetry env info --path)"/bin/activate

        # shellcheck disable=SC1090
        source "$location"

        GREEN echo -e "Venv activated\n"
    fi

}

check_dependencies() {
    local pakage_operations

    echo "Checking all dependencies are installed"

    pakage_operations=$(poetry install --dry-run --sync --no-ansi --with=dev | grep -E '^Package operations')

    if grep -q -E "[1-9]([0-9])* install" <<<"$pakage_operations"; then
        INSTALL_DEPENDENCIES=1
        YELLOW echo -e "Missing some dependencies. They'll be installed shortly\n"
    else
        GREEN echo -e "No dependencies missing\n"
    fi
}

install_dependencies() {
    echo -e 'Installing dependencies'
    poetry install --with=dev --sync -q
    GREEN echo -e 'Installed dependencies\n'
}

run_tests() {

    activate_venv

    [[ "$INSTALL_DEPENDENCIES" == 0 ]] && check_dependencies

    [[ "$INSTALL_DEPENDENCIES" == 1 ]] && install_dependencies

    ENVIRONMENT='test' poetry run python -m pytest --disable-warnings -vv

}

run_tests
