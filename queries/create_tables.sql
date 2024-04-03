CREATE TABLE IF NOT EXISTS pdl.titles
(
    id          smallint               NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 100 MINVALUE 100 MAXVALUE 1000 CACHE 1 ),
    name        character varying(100) NOT NULL,
    description text,
    CONSTRAINT pk_titles PRIMARY KEY (id)
)
    WITH (
        OIDS = FALSE
    );


CREATE TABLE IF NOT EXISTS pdl.programs
(
    id          smallint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 100 MINVALUE 100 MAXVALUE 1000 CACHE 1 ),
    title_id    smallint,
    subtitle_id smallint,
    name        character varying(100),
    CONSTRAINT pk_programs PRIMARY KEY (id)
)
    WITH (
        OIDS = FALSE
    );

CREATE TABLE IF NOT EXISTS pdl.sub_programs
(
    id         smallint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 100 MINVALUE 100 MAXVALUE 10000 CACHE 1 ),
    program_id smallint NOT NULL,
    name       character varying(100),
    CONSTRAINT pk_sub_programs PRIMARY KEY (id)
)
    WITH (
        OIDS = FALSE
    );

CREATE TABLE IF NOT EXISTS pdl.payments
(
    id              bigint               NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 100 MINVALUE 100 MAXVALUE 1000000 CACHE 1 ),
    title_id        smallint,
    subtitle_id     smallint,
    program_id      smallint,
    sub_program_id  smallint,
    state_code      character varying(2) NOT NULL,
    year            smallint             NOT NULL,
    payment         numeric(14, 2),
    recipient_count bigint,
    base_acres      numeric(10, 2),
    CONSTRAINT pk_payments PRIMARY KEY (id)
)
    WITH (
        OIDS = FALSE
    );

CREATE TABLE IF NOT EXISTS pdl.states
(
    code character varying(2)   NOT NULL,
    name character varying(100) NOT NULL,
    CONSTRAINT pk_states PRIMARY KEY (code)
)
    WITH (
        OIDS = FALSE
    );

CREATE TABLE IF NOT EXISTS pdl.statistics_view
(
    id                      bigint   NOT NULL,
    title_id                smallint,
    sub_title_id            smallint,
    program_id              smallint,
    sub_program_id          smallint,
    year                    smallint NOT NULL,
    total_payment           numeric(14, 2),
    average_recipient_count bigint,
    average_base_acres      numeric(10, 2),
    CONSTRAINT pk_statistics PRIMARY KEY (id)
)
    WITH (
        OIDS = FALSE
    );

CREATE TABLE IF NOT EXISTS pdl.programs_statistics_view
(
    program_id              smallint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 100 MINVALUE 100 MAXVALUE 1000 CACHE 1 ),
    year                    smallint,
    total_payment           numeric(14, 2),
    average_recipient_count bigint,
    average_base_acres      numeric(10, 2)
)
    WITH (
        OIDS = FALSE
    );

CREATE TABLE IF NOT EXISTS pdl.sub_programs_statistics_view
(
    sub_program_id          smallint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 100 MINVALUE 100 MAXVALUE 10000 CACHE 1 ),
    year                    smallint,
    total_payment           numeric(14, 2),
    average_recipient_count bigint,
    average_base_acres      numeric(10, 2)
)
    WITH (
        OIDS = FALSE
    );

CREATE TABLE IF NOT EXISTS pdl.subtitles
(
    id       smallint               NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 100 MINVALUE 100 MAXVALUE 1000 ),
    title_id smallint               NOT NULL,
    name     character varying(100) NOT NULL,
    CONSTRAINT pk_subtitles PRIMARY KEY (id)
)
    WITH (
        OIDS = FALSE
    );

ALTER TABLE IF EXISTS pdl.programs
    ADD CONSTRAINT "fk_ titles_id" FOREIGN KEY (title_id)
        REFERENCES pdl.titles (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
        NOT VALID;


ALTER TABLE IF EXISTS pdl.programs
    ADD CONSTRAINT "fk_ subtitles_id" FOREIGN KEY (subtitle_id)
        REFERENCES pdl.subtitles (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
        NOT VALID;


ALTER TABLE IF EXISTS pdl.sub_programs
    ADD CONSTRAINT fk_programs_id FOREIGN KEY (program_id)
        REFERENCES pdl.programs (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
        NOT VALID;


ALTER TABLE IF EXISTS pdl.payments
    ADD CONSTRAINT fk_programs_id FOREIGN KEY (program_id)
        REFERENCES pdl.programs (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
        NOT VALID;


ALTER TABLE IF EXISTS pdl.payments
    ADD CONSTRAINT fk_sub_programs_id FOREIGN KEY (sub_program_id)
        REFERENCES pdl.sub_programs (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
        NOT VALID;


ALTER TABLE IF EXISTS pdl.payments
    ADD CONSTRAINT fk_states_id FOREIGN KEY (state_code)
        REFERENCES pdl.states (code) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
        NOT VALID;


ALTER TABLE IF EXISTS pdl.payments
    ADD CONSTRAINT fk_titles_id FOREIGN KEY (title_id)
        REFERENCES pdl.titles (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID;


ALTER TABLE IF EXISTS pdl.payments
    ADD CONSTRAINT fk_subtitles_id FOREIGN KEY (subtitle_id)
        REFERENCES pdl.subtitles (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID;

-- ALTER TABLE IF EXISTS pdl.payments
--     ADD CONSTRAINT payments_unique_constraint UNIQUE (title_id, subtitle_id, program_id, sub_program_id, state_code, year)
--         NOT VALID;

ALTER TABLE IF EXISTS pdl.statistics_view
    ADD CONSTRAINT fk_programs_id FOREIGN KEY (program_id)
        REFERENCES pdl.programs (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID;


ALTER TABLE IF EXISTS pdl.statistics_view
    ADD CONSTRAINT fk_sub_programs_id FOREIGN KEY (sub_program_id)
        REFERENCES pdl.sub_programs (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID;


ALTER TABLE IF EXISTS pdl.statistics_view
    ADD CONSTRAINT fk_titles_id FOREIGN KEY (title_id)
        REFERENCES pdl.titles (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID;


ALTER TABLE IF EXISTS pdl.statistics_view
    ADD CONSTRAINT fk_subtitles_id FOREIGN KEY (sub_title_id)
        REFERENCES pdl.subtitles (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID;


ALTER TABLE IF EXISTS pdl.programs_statistics_view
    ADD CONSTRAINT fk_programs_id FOREIGN KEY (program_id)
        REFERENCES pdl.programs (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID;


ALTER TABLE IF EXISTS pdl.sub_programs_statistics_view
    ADD CONSTRAINT fk_sub_programs_id FOREIGN KEY (sub_program_id)
        REFERENCES pdl.sub_programs (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID;


ALTER TABLE IF EXISTS pdl.subtitles
    ADD CONSTRAINT fk_titles_id FOREIGN KEY (title_id)
        REFERENCES pdl.titles (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
        NOT VALID;

CREATE VIEW pdl.statistics
AS
SELECT payments.title_id,
       payments.subtitle_id,
       payments.program_id,
       payments.sub_program_id,
       payments.state_code,
       payments.year,
       sum(payments.payment)                AS total_payment,
       round(avg(payments.recipient_count)) AS avg_recipient_count,
       round(avg(payments.base_acres), 2)   AS avg_base_acres
FROM pdl.payments
         JOIN pdl.titles ON payments.title_id = titles.id
         JOIN pdl.subtitles ON payments.subtitle_id = subtitles.id
         JOIN pdl.programs ON programs.id = payments.program_id
         JOIN pdl.sub_programs ON sub_programs.id = payments.sub_program_id
GROUP BY payments.title_id, payments.subtitle_id, payments.program_id, payments.sub_program_id, payments.year,
         payments.state_code
ORDER BY payments.title_id, payments.subtitle_id, payments.program_id, payments.sub_program_id, payments.year,
         payments.state_code;