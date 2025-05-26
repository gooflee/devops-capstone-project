"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_read_an_account(self):
        """It should find an account"""
        create_account = AccountFactory()
        response = self.client.post(
        BASE_URL,
        json=create_account.serialize(),
        content_type="application/json"
        )
        new_account = response.get_json()
        print(f'The id is {new_account["id"]}')
        get_url = BASE_URL +"/"+  str(new_account["id"])
        print(f'Get_url is {get_url}')
        response = self.client.get(get_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(create_account.name, data["name"])
    
    def test_account_not_found(self):
        """Test not finding an account"""
        get_url = BASE_URL+'/0'
        response = self.client.get(get_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_account_list(self):
        """Test list of accounts is returned"""
        for i in range(10):
            account = AccountFactory()
            response = self.client.post(
              BASE_URL,
              json=account.serialize(),
              content_type="application/json"
            )
        response = self.client.get("/accounts")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data),10)
    
    def test_account_list_empty(self):
        """Test returning empty list"""
        response = self.client.get("/accounts")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data),0)

    def test_account_update(self):
        """Test Update an account"""
        new_name = "Bob Smith"
        create_account = AccountFactory()
        response = self.client.post(
        BASE_URL,
        json=create_account.serialize(),
        content_type="application/json"
        )
        new_account = response.get_json()
        new_account["name"] = new_name
        
        put_url = BASE_URL+'/'+str(new_account["id"])
        verify_response = self.client.get(put_url)
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        response = self.client.put(
            put_url, 
            json=new_account,
            content_type="application/json"
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], new_name)

    def test_account_update_no_account(self):
        """Test Update an account with no account"""
        new_name = "Bob Smith"
        create_account = AccountFactory()
        response = self.client.post(
        BASE_URL,
        json=create_account.serialize(),
        content_type="application/json"
        )
        new_account = response.get_json()
        new_account["name"] = new_name
        put_url = BASE_URL+'/0'
        response = self.client.put(
            put_url, 
            json=new_account,
            content_type="application/json"
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_account_delete(self):
        create_account = AccountFactory()
        response = self.client.post(
        BASE_URL,
        json=create_account.serialize(),
        content_type="application/json"
        )
        new_account = response.get_json()        
        delete_url = BASE_URL+'/'+str(new_account["id"])
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_not_allowed(self):
        response = self.client.delete(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_post_allowed(self):
        response = self.client.post(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_post_allowed(self):
        response = self.client.put(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)