#!/bin/bash
MYFONTS=$(pdffonts -l 5 "$1" | tail -n +3 | cut -d' ' -f1 | sort | uniq)
if [ "$MYFONTS" = '' ] || [ "$MYFONTS" = '[none]' ]; then
    echo "NOT OCR'ed: $1"
else 
    echo "$1 is OCR'ed."
fi 
