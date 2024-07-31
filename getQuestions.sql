SELECT
    q.ID AS question_id,
    q.Question,
    q.this_doesnt_seem_right,
    GROUP_CONCAT(o.optionText ORDER BY o.id ASC SEPARATOR '<MY_SEPARATOR>') AS options,
    ao.optionText AS answer_text,
    CASE
        WHEN sao.optionText IS NULL AND q.this_doesnt_seem_right = 1 THEN 'This Question Doesn''t seem right'
        ELSE sao.optionText
    END AS student_answer
FROM
    question q
JOIN
    questionOption qo
ON
    q.id = qo.question_id
JOIN
    optionTable o
ON
    qo.option_id = o.id
LEFT JOIN
    optionTable ao
ON
    q.answer = ao.id  -- Join to get the answer text
LEFT JOIN
    optionTable sao
ON
    q.StudentAnswer = sao.id  -- Join to get the student answer text
WHERE
    q.attemptID = 13
GROUP BY
    q.id, q.Question;