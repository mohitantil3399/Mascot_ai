Doing this project I faced several issues to make it work and I tried my best fix them as follows :

## 1 
**Connecting to the LLM** 
I was not able to retrieve and display the proper response from the LLM and the code was throwing errors related to the API keys and 
**Reason for the Error**
The main reason for the error was the incorrect or missing API key. The API key is a secret key that is used to authenticate the request to the LLM. 

### Solution 

I fixed it by adding the correct API keys in environment file and also tried to fix the JSON format to get the proper response from the LLM.

## 2
**Making a transparent overlay for front-end**
I had to fit in a web-based interface to run the front-end of the project in windows desktop using webview2 , It was a big challege to make it work and display the 3d mascot with the chat interface overlayed on the desktop.
## Solution 
I fixed it using the webview2 control in c# and setting the WS_EX_LAYERED style to make the window transparent and also setting the WS_EX_TRANSPARENT style to make the window click-through. 

## 3 
**Taking Screenshots of the screen**
I had to capture the entire screen and send it to the LLM for processing, It was a big challege to capture the entire screen and send it to the LLM for processing.
## Solution 
I fixed it using the ScreenCapture class in c# and setting the WS_EX_LAYERED style to make the window transparent and also setting the WS_EX_TRANSPARENT style to make the window click-through. 

## 4 
**Displaying the chat bubble only when needed**
The chat bubble was always on screen along with the pet which was not good for the user experience.
### Solution 
I fixed it by making the pet clickable , and set double click -> open the chat bubble and double click again -> close the chat bubble . I added delay in between the click so that logic for single click and double click do not conflict.

## 5 
**Making the pet moveable**
The pet was not moveable and was stuck in one place which was not good for the user experience.
### Solution 
I fixed it by making the pet moveable using the mouse drag and drop feature. Moving the entire small front-end window over the transparent underlay written in c# as making the pet only movable did not let me access underling windows original window of my workspace .This was because webview2 wrapped the entire browser window with the overlay which was not click-through.

## 6 
**Persistent memory for the assistant**
The assistant was not able to remember the previous conversation and was always starting fresh with the same context .
## Solution 
I fixed it by adding a persistent memory feature to the assistant which stores the previous conversation in a list of dictionaries that holds the current context conversations for the assistant in the ongoing session .

## 7 
**Fresh context**
Whenver the chat bubble was closed it must not hold previous chat history to not let it conflict with new idea.
## Solution 
Added sessions of conversation , making a session limited to one time interaction that holded the context of only the very ongoing chat . It reloads at every next interaction .

## 8 
**How to launch all three different programs for AI assistant in windows**
It was difficult for the user to launch all three different programs for AI assistant in windows separately. We had to make it easier for the user to launch all three different programs for AI assistant in windows .
## Solution 
I fixed it by adding a launch_all.bat file that launches the assistant and also gives a short description of each task.