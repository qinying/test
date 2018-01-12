CREATE TABLE session (
	id integer primary key, 
	site string, 
	username string,
    session string,
    create_at integer
);
CREATE UNIQUE INDEX session_idx ON session(site, username);

CREATE TABLE upload (
	id integer primary key, 
	site string, 
	local string,
    upload string
);
CREATE UNIQUE INDEX upload_idx ON upload(site, local);