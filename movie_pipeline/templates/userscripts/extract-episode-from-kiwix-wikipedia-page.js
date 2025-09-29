const seasonHeaders = document.querySelectorAll('[id*="aison_"]') // 'Saison 1' or 'Première saison'
const episodeHeaders = document.querySelectorAll('[id^="Épisode_"]')

const seasonRegExp = RegExp(/Saison (\d+)/)
const ordinalNumbers = [
  undefined,
  'Première',
  'Deuxième',
  'Troisième',
  'Quatrième',
  'Cinquième',
  'Sixième',
  'Septième'
]

function padNumber(number, length) {
  return number.toString().padStart(length, '0')
}

function getEpisodeEntriesFromSeasonHeaders() {
  return Array.from(seasonHeaders).flatMap(seasonHeader => {
    const seasonNumber = +seasonRegExp.exec(seasonHeader.textContent)?.at(1)
      || ordinalNumbers.findIndex(ordinalNumber => seasonHeader.textContent.includes(ordinalNumber))

    const details = seasonHeader.parentElement.parentElement
    let detailsContentChildren

    if ((detailsContentChildren = details.getElementsByTagName('table')).length) {
      const firstTableHeaders = Array.from(detailsContentChildren[0].getElementsByTagName('tr')[0].getElementsByTagName('th'))
      const titleHeaderIndex = firstTableHeaders.findIndex(_ => _.textContent.startsWith('Titre'))
      const episodeNumberIndex = firstTableHeaders.findIndex(_ =>  _.textContent.startsWith('No'))

      return Object.fromEntries(
        Array.from(detailsContentChildren)
          .flatMap(detailsContent => Array.from(detailsContent.getElementsByTagName('tr')))
          .filter(row => row.children?.length > 1 && row.children[titleHeaderIndex]?.children?.length)
          .map(row => [
            row.children[titleHeaderIndex].children[0].textContent,
            { formattedEpisode: `S${padNumber(seasonNumber, 2)}E${padNumber(row.children[episodeNumberIndex].textContent, 2)}` }
          ])
      )
    }

    if ((detailsContentChildren = details.querySelectorAll('ol > li')).length) {
      return Object.fromEntries(
        Array.from(detailsContentChildren).map((episodeTitle, i) => [
          episodeTitle.textContent.split(' (')[0],
          { formattedEpisode: `S${padNumber(seasonNumber, 2)}E${padNumber(i + 1, 2)}` }
        ])
      )
    }
  })
}

function getEpisodeEntriesFromEpisodeHeaders() {
  const titleContent = document.querySelector('#firstHeading').textContent
  const titleSeasonNumber = +seasonRegExp.exec(titleContent)?.at(1)

  return Array.from(episodeHeaders).map(episodeHeader => {
    const getEpisodeSeasonHeader = () => episodeHeader.parentElement.parentElement.parentElement.querySelector('[id*="Saison_"]').textContent
    const seasonNumber = titleSeasonNumber || +seasonRegExp.exec(getEpisodeSeasonHeader())[1]
    const episodeTitle = episodeHeader.textContent.split(':')[1].trim()
    const episodeNumber = +episodeHeader.textContent.split(':')[0].replace('Épisode ', '')
    const details = episodeHeader.parentElement.parentElement

    return {
      [episodeTitle]: {
        formattedEpisode: `S${padNumber(seasonNumber, 2)}E${padNumber(episodeNumber, 2)}`,
        detailledSummary: Array.from(details.children[1].querySelectorAll('b'))
          .find(field => field.textContent === 'Résumé détaillé')
          ?.nextElementSibling?.nextElementSibling?.textContent?.trim()
      }
    }
  })
}

function getEpisodeEntries() {
  const entries = []
  if (seasonHeaders.length) entries.push(...getEpisodeEntriesFromSeasonHeaders())
  if (episodeHeaders.length) entries.push(...getEpisodeEntriesFromEpisodeHeaders())

  return entries
    .filter(Boolean)
    .flatMap(_ => Object.entries(_))
    .sort((a, b) => a[1].formattedEpisode.localeCompare(b[1].formattedEpisode))
}

const episodes = Object.fromEntries(getEpisodeEntries())

console.log(JSON.stringify(episodes))
