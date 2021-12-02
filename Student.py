class Student:
    _name: str
    _email: str
    _homePhone: int
    _campusPhone: int
    _campusAddress: list
    _homeAddress: list

    def __init__(self, name, email, homePhone, campusPhone, campusAddress, homeAddress):
        self.name = name
        self.email = email
        self.homePhone = homePhone
        self.campusPhone = campusPhone
        self.campusAddress = campusAddress
        self.homeAddress = homeAddress
    
    def toString(self):
        return (f'{self.name},{self.email},{self.homePhone},{self.campusPhone},{self.campusAddress},{self.homeAddress}')