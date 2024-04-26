export const textInputProblemXml = `<problem>
  <stringresponse answer="Correct answer 1" type="ci regexp">
    <label>Question text</label>
    <description>Optional tip</description>
    <correcthint>Provides feedback when learners submit the correct response.</correcthint>
    <additional_answer answer="Correct answer 2"/>
    <additional_answer answer="Correct answer 3"/>
    <stringequalhint answer="Incorrect answer 1">Provides feedback when learners submit the specified incorrect response.</stringequalhint>
    <stringequalhint answer="Incorrect answer 2">Provides feedback when learners submit the specified incorrect response.</stringequalhint>
    <textline size="20" trailing_text="ttext1" />
    <solution>
      <p>Explanation</p>
      <p>Explanation 123</p>
    </solution>
  </stringresponse>
</problem>`
