A Python app for finding where to meet.

To load environment variables from your local .env file into uv, add the following to your .zshrc:

``` sh
# load .env if it exists in the current directory
_set_uv_env_file() {
    if [-f .env]; then
        export UV_ENV_FILE=.env
    else
        unset UV_ENV_FILE
    fi
}

# reset when changing directories
autoload -U add-zsh-hook
add-zsh-hook chpwd _set_uv_env_file

# set initially
_set_uv_env_file
```