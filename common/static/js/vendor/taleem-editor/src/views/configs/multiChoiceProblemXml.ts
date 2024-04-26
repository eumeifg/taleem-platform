export const multiChoiceProblemXml = `<problem>
  <multiplechoiceresponse>
    <label>Question or prompt text</label>
    <description>Optional information about how to answer the question</description>
    <choicegroup type="MultipleChoice">
      <choice correct="false" name="a">Incorrect choice
        <choicehint>Hint for incorrect choice.</choicehint>
      </choice>
      <choice correct="true" name="b">Correct choice
        <choicehint>Hint for correct choice.</choicehint>
      </choice>
    </choicegroup>
    <solution>
      <p>Optional header for the explanation or solution</p>
      <p>Optional explanation or solution text</p>
    </solution>
  </multiplechoiceresponse>
</problem>`
