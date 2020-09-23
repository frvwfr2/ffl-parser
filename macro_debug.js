// For each selected drawing
canvas.drawings.controlled.forEach((drawing) => {
  // Store x, y of this drawing
  let x, y = drawing.data.x, drawing.data.y;
  // If it doesn't contain an @, just ignore it completely
  if (!("text" in drawing.data) || drawing.data.text.indexOf("@") === -1) {
    ui.notifications.warn("Unused drawing selected");
  }
  // ENABLE
  else if (drawing.data.text.startsWith("_")) {
    // remove the first character, and make it green
    drawing.update({text : drawing.data.text.substring(1),
                    strokeColor : "#28cc66"});
    // Loop through tiles, see if any are similar to this drawing
    canvas.tiles.objects.children.forEach((tile) => {
      // If the tile and the drawing are in similar locations...
      if (abs(tile.data.x - x) < 30 && abs(tile.data.y - y) < 30) {
        tile.update({hidden : false});
      };
    });

    ui.notifications.info("Enabled teleporter")
  // DISABLE 
  } else {
    // add an underscore, and make it red
    drawing.update({text : "_" + drawing.data.text,
                    strokeColor : "#ff0000"});
    // Loop through tiles, see if any are similar to this drawing
    canvas.tiles.objects.children.forEach((tile) => {
      // If the tile and the drawing are in similar locations...
      if (abs(tile.data.x - x) < 30 && abs(tile.data.y - y) < 30) {
        tile.update({hidden : true});
      };
    });
    ui.notifications.info("Disabled teleporter")
  }
});