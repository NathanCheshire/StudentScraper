class Student:
    _name: str
    _email: str
    _phone: str
    _campusAddress: str
    _homeAddress: str

    def __init__(self, name, email, phone, campusAddress, homeAddress):
        self.name = name
        self.email = email
        self.phone = phone
        self.campusAddress = campusAddress
        self.homeAddress = homeAddress
    
    def toString(self):
        #todo null checks
        return (f'{self.name},{self.email},{self.phone},{self.campusAddress},{self.homeAddress}')