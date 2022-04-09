--test to make sure ' escaping is working
select * from students where homestreet like '%Popp%';
select count(*) from students;
select * from students where netid like '%107';
select * from students where isretired = 'yes';
select * from students where firstname = 'Nathan';