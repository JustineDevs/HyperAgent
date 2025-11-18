#!/bin/zsh
# HyperAgent CLI Zsh completion script
# Install: source scripts/completion/zsh.sh
# Or add to ~/.zshrc: source /path/to/scripts/completion/zsh.sh

_hyperagent() {
    local state
    _arguments \
        '1: :->command' \
        '2: :->subcommand' \
        '*: :->args'
    
    case $state in
        command)
            _values "commands" \
                "workflow[Workflow management]" \
                "contract[Contract management]" \
                "deployment[Deployment management]" \
                "system[System commands]" \
                "network[Network information]" \
                "config[Configuration]" \
                "template[Template management]" \
                "quick[Quick actions]" \
                "stats[Statistics]"
            ;;
        subcommand)
            case $words[2] in
                workflow)
                    _values "workflow commands" \
                        "create[Create workflow]" \
                        "status[Check status]" \
                        "cancel[Cancel workflow]" \
                        "list[List workflows]" \
                        "export[Export workflow]"
                    ;;
                network)
                    _values "network commands" \
                        "list[List networks]" \
                        "info[Network info]" \
                        "features[Show features]" \
                        "test[Test network]"
                    ;;
                template)
                    _values "template commands" \
                        "list[List templates]" \
                        "show[Show template]" \
                        "search[Search templates]"
                    ;;
                config)
                    _values "config commands" \
                        "show[Show config]" \
                        "validate[Validate config]"
                    ;;
            esac
            ;;
        args)
            case $words[2] in
                workflow)
                    case $words[3] in
                        create)
                            _arguments \
                                '--description[Description]' \
                                '--interactive[Interactive mode]' \
                                '--watch[Watch progress]' \
                                '--network[Network]:network:(hyperion_testnet hyperion_mainnet mantle_testnet mantle_mainnet)' \
                                '--type[Type]:type:(ERC20 ERC721 ERC1155 Custom)'
                            ;;
                        status)
                            _arguments \
                                '--workflow-id[Workflow ID]' \
                                '--watch[Watch progress]' \
                                '--format[Format]:format:(table json yaml compact)'
                            ;;
                    esac
                    ;;
            esac
            ;;
    esac
}

compdef _hyperagent hyperagent

