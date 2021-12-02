class Student:
    _name: str
    _email: str
    _phone: list
    _campusAddress: list
    _homeAddress: list

    def __init__(self, name, email, phone, campusAddress, homeAddress):
        self.name = name
        self.email = email
        self.phone = phone
        self.campusAddress = campusAddress
        self.homeAddress = homeAddress
    
    def toString(self):
        return (f'{self.name},{self.email},{self.phone},{self.campusAddress},{self.homeAddress}')