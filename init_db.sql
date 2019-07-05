CREATE TABLE articles (
    pubmed_id INTEGER PRIMARY KEY,   
    abstract TEXT,   
    pub_year INTEGER,   
    title TEXT   
);

CREATE TABLE article_authors (   
    pubmed_id INTEGER REFERENCES articles(pubmed_id),   
    f_name TEXT,   
    l_name TEXT,   
    affiliation TEXT,   
    UNIQUE(pubmed_id, f_name, l_name)   
);

CREATE TABLE article_mesh (   
    pubmed_id INTEGER REFERENCES articles(pubmed_id),   
    mesh TEXT,   
    UNIQUE(pubmed_id, mesh)   
);

CREATE TABLE authors (   
    f_name TEXT,   
    l_name TEXT,   
    UNIQUE(f_name, l_name)   
);

CREATE INDEX mesh_index ON article_mesh (mesh);
CREATE INDEX article_author_f_name_index ON article_authors(f_name);
CREATE INDEX art_auth_l_name_index ON article_authors(l_name);