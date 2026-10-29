-- Milestone I: Database schema for Resale Real Estate Application
-- Generated based on project specifications
-- ------------------------------------------------------------
-- Users table
CREATE TABLE `User` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `username` VARCHAR(100) NOT NULL UNIQUE,
    `gender` ENUM('Male','Female','Other') NOT NULL,
    `age` INT NOT NULL,
    `birthdate` DATE NOT NULL,
    `focus_areas` TEXT, -- comma‑separated list of area names
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Developers table
CREATE TABLE `Developer` (
    `developer_id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL UNIQUE,
    `description` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Locations table (city → district → area)
CREATE TABLE `Location` (
    `location_id` INT AUTO_INCREMENT PRIMARY KEY,
    `city` VARCHAR(100) NOT NULL,
    `district` VARCHAR(100),
    `area` VARCHAR(100),
    UNIQUE KEY `uq_city_district_area` (`city`,`district`,`area`),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Developments (projects) table
CREATE TABLE `Development` (
    `development_id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `description` TEXT,
    `location_id` INT NOT NULL,
    `developer_id` INT NOT NULL,
    FOREIGN KEY (`location_id`) REFERENCES `Location`(`location_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (`developer_id`) REFERENCES `Developer`(`developer_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY `uq_development_name_location` (`name`,`location_id`),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Amenities lookup table
CREATE TABLE `Amenity` (
    `amenity_id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Properties table (non‑user data)
CREATE TABLE `Property` (
    `property_id` INT AUTO_INCREMENT PRIMARY KEY,
    `development_id` INT NOT NULL,
    `location_id` INT NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `description` TEXT,
    `url` VARCHAR(500) NOT NULL UNIQUE,
    `area_sqm` DECIMAL(10,2),
    `bedrooms` TINYINT,
    `bathrooms` TINYINT,
    `property_type` ENUM('Apartment','Villa','Townhouse','Duplex','Penthouse','Chalet','Studio','Other') NOT NULL,
    `floor` INT,
    `finishing` VARCHAR(255),
    `contract_year` YEAR,
    `listing_date` DATE,
    `asking_price` DECIMAL(12,2),
    `market_price` DECIMAL(12,2),
    `down_payment` DECIMAL(12,2),
    `payment_method` ENUM('Cash','Installment'),
    `gain_over_market` DECIMAL(12,2),
    FOREIGN KEY (`development_id`) REFERENCES `Development`(`development_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (`location_id`) REFERENCES `Location`(`location_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Junction table for many‑to‑many Property ↔ Amenity
CREATE TABLE `PropertyAmenity` (
    `property_id` INT NOT NULL,
    `amenity_id` INT NOT NULL,
    PRIMARY KEY (`property_id`,`amenity_id`),
    FOREIGN KEY (`property_id`) REFERENCES `Property`(`property_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (`amenity_id`) REFERENCES `Amenity`(`amenity_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Reviews table (user ↔ development)
CREATE TABLE `Review` (
    `review_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `development_id` INT NOT NULL,
    `rating` TINYINT NOT NULL CHECK (`rating` BETWEEN 1 AND 10),
    `comment` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `User`(`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (`development_id`) REFERENCES `Development`(`development_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY `uq_user_development` (`user_id`,`development_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- End of schema

