import LiveClassroom from '@components/LiveLearning/LiveClassroom'

// Single-tenancy LearnHouse routes remain org-agnostic. In multi-tenancy this
// page is served on the current organization subdomain, so a relative leave
// link still stays inside the right organization.
export default async function LiveClassroomPage({ params }: { params: Promise<{ sessionuuid: string }> }) {
  const { sessionuuid } = await params
  return <LiveClassroom orgslug="" sessionUuid={sessionuuid} />
}
