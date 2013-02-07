/* Enables Drag 'n Drop a la Spotify Playlist.
   Used for dragging positions into career paths */


/* This in itself does nothing, just allows an element to 
   be dragged over it. Should probably but this on the entire page
   so that the '+' sign occurs during drag. More intuitive
   that way */
  function allowDrop(ev) {
  	ev.preventDefault();
  };


/* Determines what data is transferred with the drag.
   This particular method is specific to career paths. */
  function drag(ev) {
  	ev.dataTransfer.setData("pos_id", ev.target.id);
  };


/* Takes information from the element dragged and element
   dragged into in order to add the position to the given
   career path. */

   // NO LONGER USED IN PROFILE.HTML
  function drop(ev, path_title) {
  	ev.preventDefault();
  	var pos_id = ev.dataTransfer.getData("pos_id");
  	
  	// window.location='/saved_paths/create/' + path_title + '/' + pos_id + '/'	
  };