/*user table*/
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY, 
    name VARCHAR(30), 
    user_id VARCHAR(21) NOT NULL, 
    token VARCHAR(255), 
    login INT,  
    read_access INT, 
    write_access INT, 
    UNIQUE (user_id)  
);


/*plant table */
CREATE TABLE plant (
    id INT AUTO_INCREMENT PRIMARY KEY, 
    plantname VARCHAR(255) NOT NULL, 
    waterrequirement VARCHAR(50), 
    planttype VARCHAR(100), 
    plantlocation VARCHAR(255),
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(21),  
    gmail VARCHAR(255),  
    FOREIGN KEY (user_id) REFERENCES user(user_id)  -- Foreign key constraint on user_id
);