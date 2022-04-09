CREATE TABLE students (
    netid character varying NOT NULL,
    PRIMARY KEY (netid),

    -- actually useful stuff we'll primarily display
    -- in the DeckGL render
    email character varying,
    firstname character varying,
    lastname character varying,
    major character varying,
    class character varying,

    -- phone numbers
    homephone bigint,
    officephone bigint,

    -- random stuff we'll hardly access
    pidm integer,
    selected character varying,
    isstudent character varying,
    isaffiliate character varying,
    isretired character varying,
    picturepublic character varying,
    pictureprivate character varying,

    -- these are the ones we'll convert to lat/lon using MapQuest
    -- we can also use them in combo with DeckGL for some sweet rendering
    homestreet character varying,
    homecity character varying,
    homestate character varying,
    homezip character varying,
    homecountry character varying,

    -- the lat,lon coordinate precision generated from MapQuest
    -- used for heatmap renders and other PyDeck maps
    lat double precision,
    lon double precision,

    -- I don't even know why MSU has this in here 
    -- for students
    officestreet character varying,
    officecity character varying,
    officestate character varying,
    officezip character varying,
    officecountry character varying
);
