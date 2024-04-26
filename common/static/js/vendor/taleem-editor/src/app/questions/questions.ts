import { Checkboxes } from '@/app/questions/checkboxes/Checkboxes'
import { MultiChoice } from '@/app/questions/multi-choice/MultiChoice'
import { NumericalInput } from '@/app/questions/numerical-input/NumericalInput'
import { Dropdown } from '@/app/questions/dropdown/Dropdown'
import { TextInput } from '@/app/questions/text-input/TextInput'
import { MathExpression } from '@/app/questions/math-expression/MathExpression'

export const questions = {
  [Checkboxes.id]: Checkboxes,
  [Dropdown.id]: Dropdown,
  [MultiChoice.id]: MultiChoice,
  [NumericalInput.id]: NumericalInput,
  [TextInput.id]: TextInput,
  [MathExpression.id]: MathExpression,
}

export const xmlNameMap = Object.values(questions).reduce((prev, next) => ({
  ...prev,
  [next.xmlName]: next,
}), {})
