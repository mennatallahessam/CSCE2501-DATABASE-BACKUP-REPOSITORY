"""
etl/seed_users.py – Generate synthetic User rows using Faker and insert them into MySQL.
"""
import importlib.util, pathlib, pymysql, random
from faker import Faker

# Load config
config_path = pathlib.Path(__file__).resolve().parents[1] / 'config.py'
spec = importlib.util.spec_from_file_location('config', config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

fake = Faker('en_US')
Faker.seed(config.FAKER_SEED)
random.seed(config.FAKER_SEED)

AREAS = ['New Cairo', 'Maadi', 'Zamalek', 'Sheikh Zayed', '6th October', 'Heliopolis', 'Nasr City', 'Rehab', 'Tagamoa']
GENDERS = ['Male', 'Female', 'Other']

def generate_users(n=50):
    users = []
    for _ in range(n):
        gender = random.choice(GENDERS)
        bday = fake.date_of_birth(minimum_age=18, maximum_age=70)
        focus = random.sample(AREAS, k=random.randint(1, 3))
        users.append({
            'email': fake.unique.email(),
            'username': fake.unique.user_name(),
            'gender': gender,
            'age': (2026 - bday.year),
            'birthdate': bday.strftime('%Y-%m-%d'),
            'focus_areas': ','.join(focus),
        })
    return users

def seed():
    conn = pymysql.connect(
        host=config.DB_HOST, port=config.DB_PORT,
        user=config.DB_USER, password=config.DB_PASSWORD,
        database=config.DB_NAME, charset='utf8mb4', autocommit=False
    )
    sql = """
    INSERT IGNORE INTO `User` (email, username, gender, age, birthdate, focus_areas)
    VALUES (%(email)s, %(username)s, %(gender)s, %(age)s, %(birthdate)s, %(focus_areas)s)
    """
    try:
        users = generate_users(50)
        with conn.cursor() as cur:
            cur.executemany(sql, users)
        conn.commit()
        print(f"Seeded {len(users)} synthetic users into the User table.")
    except Exception as e:
        conn.rollback()
        print('Error seeding users:', e)
    finally:
        conn.close()

if __name__ == '__main__':
    seed()

