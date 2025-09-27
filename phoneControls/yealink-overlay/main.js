const { app, BrowserWindow, screen, Tray, Menu } = require('electron');
const path = require('path');

let win;
let tray;
let isQuiting = false;

function createWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;

  win = new BrowserWindow({
    width: 48,
    height: 240,
    x: width - Math.floor(100 * 0.6),
    y: height - 100,
    frame: false,
    alwaysOnTop: true,
    resizable: false,
    transparent: true,
    skipTaskbar: true,
    type: 'toolbar',
    webPreferences: {
      nodeIntegration: false
    }
  });

  win.loadURL('http://localhost:8080/overlay');

  // Prevent minimize and close from quitting the app
  win.on('minimize', (event) => {
    event.preventDefault();
    win.hide();
  });

  win.on('close', (event) => {
    if (!isQuiting) {
      event.preventDefault();
      win.hide();
    }
  });
}

app.whenReady().then(() => {
  createWindow();

  // Create tray icon
  tray = new Tray(path.resolve(__dirname, '..', 'resources', 'tray-icon.png'));
  tray.setToolTip('Overlay Controls');

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show Overlay',
      click: () => win.show()
    },
    {
      label: 'Hide Overlay',
      click: () => win.hide()
    },
    {
      label: 'Quit',
      click: () => {
        isQuiting = true;
        app.quit();
      }
    }
  ]);

  tray.setContextMenu(contextMenu);

  // Optional: click tray icon to toggle visibility
  tray.on('click', () => {
    win.isVisible() ? win.hide() : win.show();
  });
});

app.on('window-all-closed', () => {
  // Prevent quitting so tray stays alive
});
