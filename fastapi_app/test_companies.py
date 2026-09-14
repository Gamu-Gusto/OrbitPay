from routers.companies import create_company
from orm_models import AccountantAssignment, Company
from schemas import CompanyCreate


class FakeSession:
    def __init__(self):
        self.added = []
        self.flushed = False
        self.committed = False

    def add(self, value):
        self.added.append(value)

    def flush(self):
        self.flushed = True
        self.added[0].id = 42

    def commit(self):
        self.committed = True

    def refresh(self, value):
        pass

    def rollback(self):
        pass


class FakeUser:
    id = 7
    role_names = ["accountant"]


def test_accountant_is_assigned_to_company_they_create():
    db = FakeSession()

    company = create_company(CompanyCreate(name="New Client"), db=db, user=FakeUser())

    assert isinstance(company, Company)
    assert db.flushed is True
    assert db.committed is True
    assert len(db.added) == 2
    assignment = db.added[1]
    assert isinstance(assignment, AccountantAssignment)
    assert assignment.accountant_user_id == FakeUser.id
    assert assignment.company_id == company.id
