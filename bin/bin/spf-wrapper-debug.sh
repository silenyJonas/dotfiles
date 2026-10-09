#!/bin/bash
# Spustí Superfile ve /home/joncl a po zavření zůstane terminál otevřený
/usr/local/bin/spf --path /home/joncl
echo ""
echo "Superfile byl ukončen. Stiskni libovolnou klávesu pro zavření..."
read -n1 -r
