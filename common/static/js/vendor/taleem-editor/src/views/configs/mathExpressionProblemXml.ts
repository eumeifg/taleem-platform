export const mathExpressionProblemXml = `<problem>
  <formularesponse type="ci" samples="R_1,R_2,R_3@1,2,3:3,4,5#10"  answer="$computed_response">
    <label>Problem text</label>
    <responseparam type="tolerance" default="0.00001"/>
    <formulaequationinput size="20" />

<script type="loncapa/python">
computed_response = PYTHON SCRIPT
</script>

    <solution>
      <p>Explanation or solution header</p>
    </solution>
  </formularesponse>
</problem>`
