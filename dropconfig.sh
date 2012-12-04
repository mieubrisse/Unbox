# ================================
#            DropConfig
#       mieubrisse, 12/4/2012
# ==+++===========================

# Necessary stuff
shopt -s extglob
source "dropconfig_vars.sh"
source "dropconfig_aux.sh"

MAKE_FRESH_CONFIG=false
LOAD_SUGGESTIONS=true



# Handles a user's 'setup' instruction
function dc_setup {
    # Generate a fresh .dropconfig file from resources in Dropbox
    if [ ! -f $CONFIG_FILE ]; then
        MAKE_FRESH_CONFIG=true
    fi
    if $MAKE_FRESH_CONFIG; then
        dc_generateFreshConfigFile
    fi

    # Open editor to .dropconfig file
    echo "CONFIG_FILE: "$CONFIG_FILE
    ${EDITOR:-vim} $CONFIG_FILE
    if [ $? -ne 0 ]; then
        echo -e "$WARNING_TEXT_COLORUnable to successfully edit .dropconfig file" 
        exit 1
    fi

    dc_processConfigFile $CONFIG_FILE 
}



# Handles a user's 'add' instruction to add a file to Dropbox
# 1) File to add
function dc_add {
    if [ -z $1 ]; then
        echo "$ERROR_TEXT_COLOR!! Invalid file $PATH_TEXT_COLOR$1$ERROR_TEXT_COLOR to add$DEFAULT_TEXT_COLOR"
        exit 1
    fi

}



# Process user arguments
if [ -z $1 ]; then
    echo "See 'dropconfig help' for use instructions"
    exit 1
fi
USER_COMMAND=$1
case $USER_COMMAND in
    # Handles setup instructions
    setup )
        for SETUP_MODIFIER in ${@:1}; do
            case $SETUP_MODIFIER in
                -nls|--no-load-suggestions )
                    LOAD_SUGGESTIONS=false
                    ;;
                -f|--fresh )
                    MAKE_FRESH_CONFIG=true
                    ;;
            esac
        done
        dc_setup
        ;;
    # Handles instructions for adding config files to Dropbox
    add )
        if [ -z $2 ]; then
            echo "See 'dropconfig help add' for use instructions"
            exit 1
        fi
        FILE_TO_ADD=$2
        dc_add $FILE_TO_ADD
        ;;
    update )
        dc_update
        ;;
esac
