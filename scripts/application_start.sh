#!/bin/bash

# runs bot.py in another screen
screen -dmS bonsai bash -c "cd ~/Bonsai-Discord-Bot; sudo python3 bot.py; exec sh"
echo "Successfully created Bonsai screen and ran bot.py"
