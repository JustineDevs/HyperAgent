#!/bin/bash
# HyperAgent CLI Bash completion script
# Install: source scripts/completion/bash.sh
# Or add to ~/.bashrc: source /path/to/scripts/completion/bash.sh

_hyperagent_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Main commands
    if [ ${COMP_CWORD} -eq 1 ]; then
        opts="workflow contract deployment system network config template quick stats"
        COMPREPLY=($(compgen -W "${opts}" -- ${cur}))
        return 0
    fi
    
    # Workflow subcommands
    if [ "${COMP_WORDS[1]}" == "workflow" ]; then
        case "${prev}" in
            --network|-n)
                COMPREPLY=($(compgen -W "hyperion_testnet hyperion_mainnet mantle_testnet mantle_mainnet" -- ${cur}))
                return 0
                ;;
            --type|-t)
                COMPREPLY=($(compgen -W "ERC20 ERC721 ERC1155 Custom" -- ${cur}))
                return 0
                ;;
            --format)
                COMPREPLY=($(compgen -W "table json yaml compact" -- ${cur}))
                return 0
                ;;
            --status-filter|-s)
                COMPREPLY=($(compgen -W "created generating auditing testing deploying completed failed" -- ${cur}))
                return 0
                ;;
        esac
        
        if [ ${COMP_CWORD} -eq 2 ]; then
            opts="create status cancel list export"
            COMPREPLY=($(compgen -W "${opts}" -- ${cur}))
        fi
    fi
    
    # Network subcommands
    if [ "${COMP_WORDS[1]}" == "network" ]; then
        if [ ${COMP_CWORD} -eq 2 ]; then
            opts="list info features test"
            COMPREPLY=($(compgen -W "${opts}" -- ${cur}))
        elif [ ${COMP_CWORD} -eq 3 ] && [ "${COMP_WORDS[2]}" == "info" ] || [ "${COMP_WORDS[2]}" == "features" ] || [ "${COMP_WORDS[2]}" == "test" ]; then
            COMPREPLY=($(compgen -W "hyperion_testnet hyperion_mainnet mantle_testnet mantle_mainnet" -- ${cur}))
        fi
    fi
    
    # Template subcommands
    if [ "${COMP_WORDS[1]}" == "template" ]; then
        if [ ${COMP_CWORD} -eq 2 ]; then
            opts="list show search"
            COMPREPLY=($(compgen -W "${opts}" -- ${cur}))
        fi
    fi
    
    # Config subcommands
    if [ "${COMP_WORDS[1]}" == "config" ]; then
        if [ ${COMP_CWORD} -eq 2 ]; then
            opts="show validate"
            COMPREPLY=($(compgen -W "${opts}" -- ${cur}))
        fi
    fi
    
    # Global options
    if [[ ${cur} == -* ]]; then
        opts="--help --version --verbose --debug --log-level"
        COMPREPLY=($(compgen -W "${opts}" -- ${cur}))
    fi
}

complete -F _hyperagent_completion hyperagent

