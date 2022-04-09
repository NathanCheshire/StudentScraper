CREATE TABLE faculty ( 
    netid character varying NOT NULL,
    PRIMARY KEY (netid),

    -- more random stuff we don't need
    pidm character varying,
    selected character varying,
    isstudent character varying,
    isaffiliate character varying,
    isretired character varying,
    picturepublic character varying,
    pictureprivate character varying,

    -- name information
    firstname character varying,
    lastname character varying,
    prefname character varying,
    nameprefix character varying,

    -- information relating to the faculty individual
    officephone character varying,
    email character varying,
    orgn character varying,
    title character varying,

    -- these are literally always MSU addresses
    street1 character varying,
    street2 character varying,
    city character varying,
    state character varying,
    zip character varying,
    country character varying,
);
