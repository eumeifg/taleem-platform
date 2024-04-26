export function createNewValidationError (message) {
  return {
    message,
  }
}

export interface IValidationError {
  message: string;
}
