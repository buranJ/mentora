import LiveClassroom from '@components/LiveLearning/LiveClassroom'

export default async function LiveClassroomPage({ params }: { params: Promise<{ orgslug: string; sessionuuid: string }> }) {
  const { orgslug, sessionuuid } = await params
  return <LiveClassroom orgslug={orgslug} sessionUuid={sessionuuid} />
}
