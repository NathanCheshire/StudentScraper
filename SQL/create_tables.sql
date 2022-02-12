--this is the schema for students, simply create this in your db and link the appropriate credentials to pg
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

--the schema for faculty
CREATE TABLE faculty
( netid character varying NOT NULL,
  PRIMARY KEY (netid),
  pidm character varying,
  selected character varying,
  isstudent character varying,
  isaffiliate character varying,
  isretired character varying,
  picturepublic character varying,
  pictureprivate character varying,
  firstname character varying,
  lastname character varying,
  prefname character varying,
  nameprefix character varying,
  officephone character varying,
  email character varying,
  orgn character varying,
  title character varying,
  street1 character varying,
  street2 character varying,
  city character varying,
  state character varying,
  zip character varying,
  country character varying,
);

-- the schema for both home_addresses and office_addresses, simply change the name accordingly
CREATE TABLE home_addresses
( netid character varying NOT NULL,
  PRIMARY KEY (netid),
  lat double precision,
  lon double precision,
);