SELECT ID FROM `optionTable`as OT
LEFT JOIN `questionOption`as QO ON OT.ID = QO.option_id
WHERE QO.question_id = 254 AND OT.optionText = "None of the above.";