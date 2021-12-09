--visualization ideas: heat map for USA
--number of people per state/top states for attendance
--top states with more than one confirmed student in the family (same number)
--average distance from address to MSU

--total num in database
select count(*) 
from students;

select *
from students;

--distinct majors at msu
select distinct major 
from students; 

--engineering seniors
select firstname,lastname,netid 
from students 
where class = 'Senior' and (major like '%engineering%' or major like '%Engineering%');

--art majors kek
select count(*) 
from students 
where major = 'Art';

--how many last names are repeated
select count(*) as num, lastname
from students
group by lastname
having count(lastname) > 1
order by num desc;

--student last names that start with some substring
select count(*) 
from students 
where lastname like 'C%';

--repeated phone numbers, implies families
select count(*) as num, homephone
from students
group by homephone
having count(lastname) > 1
order by num desc;

--a family of undecisive kids from Jackson lol
select * 
from students 
where homephone = '6019061788';

--helix addresses
select firstname, lastname, major, class, homestreet 
from students 
where homestreet like '%Dawg Drive%'
order by firstname,lastname;

--non null home addresses (1650 are null)
select count(*) 
from students 
where homestreet != 'NULL';

--confirm zips are valid
select distinct homezip 
from students;

--select short sample
select * 
from students 
order by firstname limit 10;

--graduating software engineers
select netid, firstname, lastname, major, class
from students
where major = 'Mechanical Engineering';

--occurneces of netid numbers
select count(*) as occurences, netidnum
from students
group by netidnum
order by netidnum asc;

--the best TA

select * 
from students
where class = 'Graduate' and firstname = 'Jesse';

--Starkville people
select netid, firstname, lastname, homestreet, class, major
from students
where homecity like '%Starkville%'
order by class;

--college view people 
select * from students 
where homestreet like '%College View%' or officestreet like '%College View%';

--transactions
begin;
commit;

--home addresses
select count(*) 
from home_addresses;

--office addresses
select count(*) 
from office_addresses;

--this should be the num in the office_addresses table after script is done
select count(*) from students where officestreet != 'NULL';

--join tables
select * 
from home_addresses 
inner join students on home_addresses.netid = students.netid;

--by state number of people
select count(*)
from students
where homestate = 'MS';

select count(*)
from students
where homestate = 'LA';

--by state visualiztion work
select count(distinct homestate)
from students;

select count(*) 
from students 
where homestate = 'DC';

--leave this space


