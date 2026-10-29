# CSCE 2501: Fundamentals of Database Systems - Project
## Milestone I: Database Design & Implementation (Detailed Specifications & Instructions)

---

## 1. Project Overview & Context
You are tasked with building a robust database backend for a real estate application focused on **Resale Properties in Egypt**. While existing platforms like [AqarExit](https://aqarexit.com/en/opportunities?show=8000) provide property listings, they lack advanced filtering capabilities, market analytics, and high-level aggregation features. 

**Milestone I** focuses exclusively on designing and establishing the foundational relational database schema using **MySQL**.

---

## 2. Detailed Data Requirements
Your database design must thoroughly capture all structural and relational aspects of the real estate resale market based on the project scope. Ensure you account for the following entities, attributes, and relationships:

### A. Properties & Property Attributes
Every property listing on the platform must store comprehensive information, including but not limited to:
*   **Unique Identifier & Core Details:** Property ID, title, description, and source URL.
*   **Physical Specifications:** Total area (sqm), number of bedrooms, number of bathrooms, property type (e.g., apartment, villa, townhouse, duplex, chalet, etc.).
*   **Financial & Contract Details:** Asking price, price per square meter, payment method (cash, installment), down payment, contract year, discount over market price, and gain over current/market value.
*   **Amenities:** A structured or relational representation of amenities associated with the property (e.g., pool, security, parking, garden, gym, etc.).

### B. Developments & Locations
Many properties belong to larger development projects. Your schema must capture:
*   **Development Projects:** Project name, description, and associated developer.
*   **Developers:** Developer name, corporate details, and tracking metrics.
*   **Locations / Areas:** Hierarchical or explicit location data (e.g., city, district, compound, area name) where developments and properties are situated.

### C. Users & Reviews
The system must support user management and community feedback:
*   **User Registration:** Users must be able to register with a unique email address, username, gender, age, birthdate, and their main areas of focus.
*   **Project Reviews:** Registered users can submit reviews for any development project, consisting of a rating on a scale of $1$ to $10$ and a textual review comment.

---

## 3. Milestone I Deliverables & Requirements
You must submit the following deliverables by **October 3rd, 2026**:

1.  **Entity-Relationship Diagram (ERD):**
    *   Provide a clear, complete, and professional ERD illustrating all entities, attributes (identifying primary keys and foreign keys), cardinalities ($1:1$, $1:N$, $M:N$), and participation constraints.
2.  **Relational Model:**
    *   Derive the clean relational schemas from your ERD. Clearly specify relations, attributes, primary keys, and foreign key constraints for each table in normalized form (at least 3NF).
3.  **MySQL Database & Schema Transcript:**
    *   Provide a fully documented and executable SQL script transcript. This script must create the database, create all tables with appropriate data types, establish proper constraints (`PRIMARY KEY`, `FOREIGN KEY`, `NOT NULL`, `CHECK` constraints like rating between 1 and 10), and ensure referential integrity.

---

## 4. Step-by-Step Implementation Instructions for Students

### Step 1: Conceptual Design (ER Diagram)
*   Identify all core entities: `User`, `Review`, `Property`, `Development`, `Developer`, `Location`, and `Amenity` (or property-amenity mapping).
*   Define attributes for each entity. Ensure multi-valued attributes (like amenities) or complex relationships (like property-to-amenities or user-to-areas-of-focus) are properly normalized using associative junction tables where necessary.
*   Establish correct relationships:
    *   A **Developer** has many **Developments**.
    *   A **Development** is located in a **Location** and has many **Properties**.
    *   A **Property** belongs to a **Development** (and/or **Location**).
    *   A **User** writes many **Reviews** for **Developments**.

### Step 2: Logical Design (Relational Schema Mapping)
*   Translate your ERD into relations.
*   Write out the relational schema schema notation clearly (e.g., `Table_Name(Attribute1, Attribute2, ...)` with underlined primary keys and italicized foreign keys).
*   Verify that your design avoids redundancy and satisfies Boyce-Codd Normal Form (BCNF) or 3NF where applicable.

### Step 3: Physical Implementation (MySQL Server)
*   Open your MySQL environment (Workbench, CLI, etc.).
*   Write an SQL script that starts with database creation and safe usage:
    ```sql
    DROP DATABASE IF EXISTS ResaleRealEstateDB;
    CREATE DATABASE ResaleRealEstateDB;
    USE ResaleRealEstateDB;
    ```
*   Create independent tables first (e.g., `Location`, `Developer`, `User`), followed by dependent tables (`Development`, `Property`, `Review`, and any lookup/junction tables).
*   Include appropriate data types (e.g., `VARCHAR`, `INT`, `DECIMAL(12,2)` for financial figures, `DATE`, `TEXT`).
*   Incorporate `ON DELETE` and `ON UPDATE` cascade/restrict rules where appropriate to maintain data integrity.

---

## 5. Evaluation Criteria & Rubric
Your submission for Milestone I will be graded out of **20 points** based on the following criteria:
*   **Completeness & Coverage (5 pts):** All required fields and constraints specified in the project description (area, location, developer, type, bedrooms/bathrooms, amenities, payment details, user info, ratings) are successfully modeled.
*   **ERD Quality & Correctness (5 pts):** Proper use of ER notation, correct cardinalities, clear identification of keys, and logical coherence.
*   **Relational Mapping & Normalization (5 pts):** Accurate derivation of relations from the ERD, proper handling of M:N relationships (e.g., amenities, user focus areas), and adherence to normalization principles.
*   **SQL Implementation & Executability (5 pts):** Clean, error-free SQL script that successfully executes on MySQL server, properly enforces primary/foreign key constraints, and includes necessary data types.