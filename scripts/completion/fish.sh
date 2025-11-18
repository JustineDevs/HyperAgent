#!/usr/bin/env fish
# HyperAgent CLI Fish completion script
# Install: cp scripts/completion/fish.sh ~/.config/fish/completions/hyperagent.fish

complete -c hyperagent -f

# Main commands
complete -c hyperagent -n '__fish_use_subcommand' -a workflow -d 'Workflow management'
complete -c hyperagent -n '__fish_use_subcommand' -a contract -d 'Contract management'
complete -c hyperagent -n '__fish_use_subcommand' -a deployment -d 'Deployment management'
complete -c hyperagent -n '__fish_use_subcommand' -a system -d 'System commands'
complete -c hyperagent -n '__fish_use_subcommand' -a network -d 'Network information'
complete -c hyperagent -n '__fish_use_subcommand' -a config -d 'Configuration'
complete -c hyperagent -n '__fish_use_subcommand' -a template -d 'Template management'
complete -c hyperagent -n '__fish_use_subcommand' -a quick -d 'Quick actions'
complete -c hyperagent -n '__fish_use_subcommand' -a stats -d 'Statistics'

# Global options
complete -c hyperagent -s h -l help -d 'Show help'
complete -c hyperagent -l version -d 'Show version'
complete -c hyperagent -s v -l verbose -d 'Verbose output'
complete -c hyperagent -s d -l debug -d 'Debug mode'
complete -c hyperagent -l log-level -d 'Log level' -xa 'DEBUG INFO WARNING ERROR'

# Workflow commands
complete -c hyperagent -n '__fish_seen_subcommand_from workflow' -a create -d 'Create workflow'
complete -c hyperagent -n '__fish_seen_subcommand_from workflow' -a status -d 'Check status'
complete -c hyperagent -n '__fish_seen_subcommand_from workflow' -a cancel -d 'Cancel workflow'
complete -c hyperagent -n '__fish_seen_subcommand_from workflow' -a list -d 'List workflows'
complete -c hyperagent -n '__fish_seen_subcommand_from workflow' -a export -d 'Export workflow'

# Workflow create options
complete -c hyperagent -n '__fish_seen_subcommand_from workflow; and __fish_seen_subcommand_from create' -s d -l description -d 'NLP description'
complete -c hyperagent -n '__fish_seen_subcommand_from workflow; and __fish_seen_subcommand_from create' -s i -l interactive -d 'Interactive mode'
complete -c hyperagent -n '__fish_seen_subcommand_from workflow; and __fish_seen_subcommand_from create' -s w -l watch -d 'Watch progress'
complete -c hyperagent -n '__fish_seen_subcommand_from workflow; and __fish_seen_subcommand_from create' -s n -l network -d 'Network' -xa 'hyperion_testnet hyperion_mainnet mantle_testnet mantle_mainnet'
complete -c hyperagent -n '__fish_seen_subcommand_from workflow; and __fish_seen_subcommand_from create' -s t -l type -d 'Contract type' -xa 'ERC20 ERC721 ERC1155 Custom'

# Network commands
complete -c hyperagent -n '__fish_seen_subcommand_from network' -a list -d 'List networks'
complete -c hyperagent -n '__fish_seen_subcommand_from network' -a info -d 'Network info'
complete -c hyperagent -n '__fish_seen_subcommand_from network' -a features -d 'Show features'
complete -c hyperagent -n '__fish_seen_subcommand_from network' -a test -d 'Test network'

# Network info/features/test arguments
complete -c hyperagent -n '__fish_seen_subcommand_from network; and __fish_seen_subcommand_from info features test' -xa 'hyperion_testnet hyperion_mainnet mantle_testnet mantle_mainnet'

