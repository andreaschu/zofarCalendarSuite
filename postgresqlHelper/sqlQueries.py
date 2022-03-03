def query_fragment_variables_for_token(token: str) -> str:
    return f"""SELECT sd.variablename, sd.value 
    FROM surveydata sd 
    WHERE sd.participant_id in 
    (SELECT p.id FROM participant p WHERE p.token = '{token}')
    AND sd.variablename like 'episodes_fragment_%'"""



distinct_pages_visited_per_token_query = '''select P.token, string_agg(distinct(SH.page), ',') 
FROM surveyhistory SH, participant P
where SH.participant_id = P.id
group by P.token;'''

all_pages_visited_per_token_query = '''select P.token, string_agg(SH.page, ',') 
FROM surveyhistory SH, participant P
where SH.participant_id = P.id
group by P.token;'''

distinct_pages_visited_overall_query = '''select string_agg(distinct(SH.page), ',') 
FROM surveyhistory SH;'''

page_visited_counts_overall_query = '''select SH.page, count(id) 
FROM surveyhistory SH 
group by SH.page 
order by SH.page;'''

page_visited_counts_overall_distinct_per_token_query = '''select SH.page, count(DISTINCT participant_id) 
FROM surveyhistory SH 
group by SH.page 
order by SH.page;'''

all_variables_filled_overall_incl_preloads_query = '''select distinct(SD.variablename)
FROM surveydata SD;'''

all_variables_filled_overall_excl_preloads_query = '''select distinct(SD.variablename)
FROM surveydata SD WHERE variablename not like 'PRELOAD%';'''
