const seasonHeaders = document.querySelectorAll('[id*="saison_"]')

function padNumber(number, length) {
  return number.toString().padStart(length, '0')
}

const episodesEntries = Array.from(seasonHeaders).flatMap((seasonHeader, index) => {
  const seasonNumber = index + 1
  const details = seasonHeader.parentElement.parentElement
  let detailsContentChildren

  if ((detailsContentChildren = details.getElementsByTagName('table')).length) {
    const [detailsContent] = detailsContentChildren
    const tableHeaders = Array.from(detailsContent.getElementsByTagName('th'))
    const titleHeaderIndex = tableHeaders.findIndex(_ => _.textContent.includes('Titre'))

    return Object.fromEntries(
      Array.from(detailsContent.getElementsByTagName('tr'))
        .filter(row => row.children[titleHeaderIndex]?.children?.length)
        .map((row, i) => [
          row.children[titleHeaderIndex].children[0].textContent,
          `S${padNumber(seasonNumber, 2)}E${padNumber(i + 1, 2)}`,
        ])
    )
  }

  if ((detailsContentChildren = details.querySelectorAll('ol > li')).length) {
    return Object.fromEntries(
      Array.from(detailsContentChildren).map((episodeTitle, i) => [
        episodeTitle.textContent.split(' (')[0],
        `S${padNumber(seasonNumber, 2)}E${padNumber(i + 1, 2)}`,
      ])
    )
  }
})

const episodes = episodesEntries.reduce((acc, val) => ({ ...acc, ...val }), {})

console.log(JSON.stringify(episodes))
