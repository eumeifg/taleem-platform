export function forceArray<K> (arrOrObj: K): Array<K> {
  if (Array.isArray(arrOrObj)) {
    return arrOrObj
  } else {
    return [arrOrObj]
  }
}
