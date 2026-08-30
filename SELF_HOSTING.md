# 🖥️ GhostQuery Local Setup Guide

This guide explains how to set up, run, and test the GhostQuery backend on your local machine.

## 1. Create Your Project Folder & Files
1. Create a new folder on your computer (e.g., `ghostquery-local`).
2. Inside this folder, create a file named `test_server.py`.
3. Paste the provided Python server code into `test_server.py` and save it.
4. Make sure your `index.html` file is also in this folder or accessible nearby.

## 2. Add `test_server.py` to GitHub (Optional)
If you want to back up your local server script to your repository:
1. Go to your `ghostquery` repository on GitHub in your web browser.
2. Click **Add file** > **Upload files**.
3. Drag and drop your `test_server.py` file into the upload box.
4. Click **Commit changes** to save it to your repository.

## 3. Install Python & Dependencies
Ensure you have Python installed on your system.
* Open your Terminal (Mac/Linux) or Command Prompt (Windows).
* Type `python3 --version` (or `python --version` on Windows) and press **Enter**.
* If you see a version number above `Python 3.10.x`, you are ready. *(If it returns an error, download the latest Python version from [python.org](https://www.python.org/downloads/)).*
* Install the required requests library by running: `pip3 install requests` (Mac/Linux) (or `pip install requests` on Windows).

## 4. Start the Local Server
1. Open your Terminal or Command Prompt.
2. Navigate to your project folder using the `cd` command (e.g., `cd path/to/your/ghostquery-folder`).
   *(Tip for Mac users: Type `cd `, space, and then drag and drop the folder from Finder into the terminal and press Enter).*
3. Run the local test server script:
   * **Mac/Linux:** `python3 test_server.py`
   * **Windows:** `python test_server.py`

4. You will see a confirmation message indicating the server is running on port `5050`:

   ```text
   ==================================================
    👻 GhostQuery Socket-Level Test Server Running
   ==================================================
    Target: [http://127.0.0.1:5050/api/search?q=linux+distros](http://127.0.0.1:5050/api/search?q=linux+distros)
    Press Ctrl+C to stop.
   --------------------------------------------------
## 5. Configure the Frontend
Now that your local backend is waiting for requests, configure your browser interface to route search requests to it:
1. Open your Terminal or Command Prompt and type in `ipconfig` (or `ipconfig getifaddr en0` for Mac) and hit **Enter**.
2. Open `index.html` in any web browser (Chrome, Safari, Firefox, Edge).
3. Click the **Network Settings** button in the top right corner.
4. Select the **Local Testing** option and type in the IP adress of the device where the server is running.
5. Click **Save Preferences**.

## 6. Test It Out!
1. Type a query into the main search bar and hit **Enter**.
2. Your browser will make requests directly to `http://127.0.0.1:5050`.
3. Check your terminal window running the Python script—you will see real-time logs as your machine queries DuckDuckGo, applies privacy obfuscation, and returns JSON results to your UI.

*(Note: Keep the terminal window running while testing locally. If you close it, local searches will fail).*