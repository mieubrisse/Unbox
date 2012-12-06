# Generates a fresh config file from Dropbox resources and defaults and stores it in the config file location
function dc_generateFreshConfigFile {
    echo -e "# Choose where each file will be linked to: LOCAL LINK PATH => TARGET (e.g. ~/.vimrc => ./.vimrc) \
    \n# To stop a link from being created to a file, delete the line or comment it out with '#'\n" > $CONFIG_FILE

    # Process files in Dropbox folder to determine which are config files can be linked to
    for FILE in `find $SRC_DIR -type f -name "*"`; do
        STRIPPED_FILE=`echo $FILE | sed "s:.*/::g"`
        TILDE_CONTRACTED_FILE=`echo $FILE | sed "s:$HOME:~:g"`
        #FULL_FILE=$SRC_DIR`echo $FILE | sed "s:.::"`
        case $STRIPPED_FILE in
        \.vimrc)
            LINK_DEST="~/.vimrc"    
            ;;
        \.bash*)
            LINK_DEST="~/$STRIPPED_FILE"
            ;;
        *)
            LINK_DEST=""
            ;;
        esac
        echo "$LINK_DEST   =>   $TILDE_CONTRACTED_FILE" >> $CONFIG_FILE    
    done
}



# Processes a .dropconfig file and forges the indicated symlinks
# 1) Path to config file to process
function dc_processConfigFile {
    # Checks argument validity
    if [ -z $1 ]; then
        echo "$ERROR_TEXT_COLOR!! One or more arguments to processConfigFile are null$DEFAULT_TEXT_COLOR"
        return 1
    fi

    # Process the user's file
    while read LINE
    do
        TRIMMED_LINE=`echo $LINE | sed -e "s/^ *//g;s/$ *//g"`
        case $TRIMMED_LINE in 
        \#*|*(\n|\ |\t) )
            # Ignore comments and whitespace lines
            ;;
        +(?)*(\ )=\>*(\ )+(?) )
            # Extract relevant parts of line and perform tilde-expansion
            LINK=`echo ${LINE%%*( )=>*} | sed "s:~:$HOME:g"`
            TARGET=`echo ${LINE##*=>*( )} | sed "s:~:$HOME:g"`

            # Evaluate whether the link should be made and keep the user informed
            if [ ! -e $TARGET ]; then
                echo -e "$ERROR_TEXT_COLOR!! Target $PATH_TEXT_COLOR$TARGET$ERROR_TEXT_COLOR does not exist$DEFAULT_TEXT_COLOR"
                PROCEED_WITH_LINK=false
            else
                # This case specifically handles  dead symlinks
                if [ ! -e $LINK -a -L $LINK ]; then
                    echo -e "$INFO_TEXT_COLOR-- Link $PATH_TEXT_COLOR$LINK$INFO_TEXT_COLOR already exists; appending '.conf_bak' to it$DEFAULT_TEXT_COLOR"
                    mv $LINK "$LINK.conf_bak"
                    PROCEED_WITH_LINK=true
                elif [ ! -e $LINK ]; then
                    PROCEED_WITH_LINK=true
                elif [ -f $LINK ]; then
                    echo -e "$INFO_TEXT_COLOR-- File $PATH_TEXT_COLOR$LINK$INFO_TEXT_COLOR already exists; appending '.conf_bak' to it$DEFAULT_TEXT_COLOR"
                    mv "$LINK" "$LINK.conf_bak"
                    PROCEED_WITH_LINK=true
                elif [ -d $LINK ]; then

                    # TODO: Allow copying of directories instead of just files

                    echo -e "$ERROR_TEXT_COLOR!! Skippping link $PATH_TEXT_COLOR$LINK$ERROR_TEXT_COLOR because it's already a directory$DEFAULT_TEXT_COLOR"
                    PROCEED_WITH_LINK=false
                else
                    echo -e "$ERROR_TEXT_COLOR!! An error occurred trying to link $PATH_TEXT_COLOR$LINK$ERROR_TEXT_COLOR with $PATH_TEXT_COLOR$TARGET$DEFAULT_TEXT_COLOR"
                    PROCEED_WITH_LINK=false
                fi
            fi
            if $PROCEED_WITH_LINK; then
                ln -s $TARGET $LINK
                if [ $? -eq 0 ]; then
                    echo -e "\e[0;32m++ Linked $PATH_TEXT_COLOR$LINK\e[0;32m to $PATH_TEXT_COLOR$TARGET$DEFAULT_TEXT_COLOR"
                else
                    echo -e "$ERROR_TEXT_COLOR!! Error linking $PATH_TEXT_COLOR$LINK$ERROR_TEXT_COLOR to $PATH_TEXT_COLOR$TARGET$DEFAULT_TEXT_COLOR"
                fi
            fi
            ;;
        * )
            echo "Error with input line: $LINE"    
            ;;
        esac
    done < $1
}
