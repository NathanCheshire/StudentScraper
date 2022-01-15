CREATE TABLE students
( netid character varying NOT NULL,
  PRIMARY KEY (netid),
  email character varying,
  firstname character varying,
  lastname character varying,
  picturepublic character varying,
  pictureprivate character varying,
  major character varying,
  class character varying,
  homephone bigint,
  officephone bigint,
  pidm integer,
  selected character varying,
  isstudent character varying,
  isaffiliate character varying,
  isretired character varying,
  homestreet character varying,
  homecity character varying,
  homestate character varying,
  homezip character varying,
  homecountry character varying,
  officestreet character varying,
  officecity character varying,
  officestate character varying,
  officezip character varying,
  officecountry character varying
);

--test to make sure ' escaping is working
select * from students where homestreet like '%Popp%';
select count(*) from students;
select * from students where netid = 'pma107';
select * from students where isretired = 'yes';
select * from students where firstname = 'Nathan';