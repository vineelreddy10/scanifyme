import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { AppLayout, PageHeader, Card } from '../components/ui/AppLayout'
import { ItemStatusBadge } from '../components/ui/StatusBadge'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import { PageLoading } from '../components/ui/LoadingSpinner'
import { SuccessBanner } from '../components/ui/ErrorBanner'
import { PrivacyBadge, RewardVisibilityBadge } from '../components/ui/TrustBadge'
import { getItemDetails, updateItemStatus, getItemRewardSettings, updateItemRewardSettings, ItemDetails, RewardSettings } from '../api/frappe'

const ItemDetail = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [item, setItem] = useState<ItemDetails | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isUpdating, setIsUpdating] = useState(false)
  const [showStatusMenu, setShowStatusMenu] = useState(false)
  const [showSuccess, setShowSuccess] = useState('')

  const [rewardSettings, setRewardSettings] = useState<RewardSettings | null>(null)
  const [showRewardEdit, setShowRewardEdit] = useState(false)
  const [rewardEnabled, setRewardEnabled] = useState(false)
  const [rewardAmountText, setRewardAmountText] = useState('')
  const [rewardNote, setRewardNote] = useState('')
  const [rewardVisibility, setRewardVisibility] = useState('Public')
  const [isSavingReward, setIsSavingReward] = useState(false)

  useEffect(() => {
    if (id) {
      loadItem()
    }
  }, [id])

  const loadItem = async () => {
    setIsLoading(true)
    try {
      const data = await getItemDetails(id!)
      if (data) {
        setItem(data)
        if (id) {
          try {
            const reward = await getItemRewardSettings(id)
            setRewardSettings(reward)
            setRewardEnabled(reward.reward_enabled)
            setRewardAmountText(reward.reward_amount_text || '')
            setRewardNote(reward.reward_note || '')
            setRewardVisibility(reward.reward_visibility || 'Public')
          } catch (rewardErr) {
            console.error('Failed to load reward settings:', rewardErr)
          }
        }
      } else {
        setError('Item not found or you do not have permission to view it')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load item')
    } finally {
      setIsLoading(false)
    }
  }

  const handleStatusChange = async (newStatus: string) => {
    if (!item) return
    
    setIsUpdating(true)
    try {
      const result = await updateItemStatus(item.id, newStatus)
      if (result.success) {
        setItem({ ...item, status: newStatus })
        setShowStatusMenu(false)
        setShowSuccess('Status updated successfully')
        setTimeout(() => setShowSuccess(''), 3000)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to update status')
    } finally {
      setIsUpdating(false)
    }
  }

  const handleSaveReward = async () => {
    if (!item) return
    
    setIsSavingReward(true)
    try {
      const result = await updateItemRewardSettings(
        item.id,
        rewardEnabled,
        rewardEnabled ? rewardAmountText : null,
        rewardEnabled ? rewardNote : null,
        null,
        rewardVisibility
      )
      if (result.success) {
        setShowRewardEdit(false)
        setRewardSettings({
          ...rewardSettings!,
          reward_enabled: rewardEnabled,
          reward_amount_text: rewardAmountText,
          reward_note: rewardNote,
          reward_visibility: rewardVisibility,
        })
        setShowSuccess('Reward settings saved')
        setTimeout(() => setShowSuccess(''), 3000)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to update reward settings')
    } finally {
      setIsSavingReward(false)
    }
  }

  const handleCancelRewardEdit = () => {
    if (rewardSettings) {
      setRewardEnabled(rewardSettings.reward_enabled)
      setRewardAmountText(rewardSettings.reward_amount_text || '')
      setRewardNote(rewardSettings.reward_note || '')
      setRewardVisibility(rewardSettings.reward_visibility || 'Public')
    }
    setShowRewardEdit(false)
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never'
    return new Date(dateStr).toLocaleString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (isLoading) {
    return (
      <AppLayout>
        <PageLoading />
      </AppLayout>
    )
  }

  if (error || !item) {
    return (
      <AppLayout>
        <PageHeader title="Item Details" />
        <ErrorBanner 
          message={error || 'Item not found'} 
          onRetry={loadItem}
        />
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <PageHeader
        title={item.item_name}
        breadcrumbs={[
          { label: 'Items', href: '/items' },
          { label: item.item_name }
        ]}
        actions={
          <div className="flex items-center gap-3">
            <div className="relative">
              <button
                onClick={() => setShowStatusMenu(!showStatusMenu)}
                disabled={isUpdating}
                className={`inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md ${
                  item.status === 'Active' ? 'bg-green-100 text-green-800' :
                  item.status === 'Lost' ? 'bg-red-100 text-red-800' :
                  item.status === 'Recovered' ? 'bg-blue-100 text-blue-800' :
                  item.status === 'Archived' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-gray-100 text-gray-800'
                } hover:opacity-80`}
              >
                {isUpdating ? 'Updating...' : item.status}
                <svg className="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {showStatusMenu && (
                <div className="absolute right-0 mt-2 w-40 bg-white rounded-md shadow-lg border z-10">
                  {['Active', 'Lost', 'Recovered', 'Archived'].filter(s => s !== item.status).map(status => (
                    <button
                      key={status}
                      onClick={() => handleStatusChange(status)}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Mark as {status}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        }
      />

      {showSuccess && <SuccessBanner message={showSuccess} />}
      {error && <ErrorBanner message={error} onDismiss={() => setError('')} />}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Item Details</h2>
            <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Item Name</dt>
                <dd className="mt-1 text-sm text-gray-900">{item.item_name}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Category</dt>
                <dd className="mt-1 text-sm text-gray-900">{item.item_category_name || '-'}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500 flex items-center gap-2">
                  Public Label
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-100 text-green-700">Public</span>
                </dt>
                <dd className="mt-1 text-sm text-gray-900">{item.public_label || '-'}</dd>
              </div>
              <div className="sm:col-span-1">
                <dt className="text-sm font-medium text-gray-500">Status</dt>
                <dd className="mt-1">
                  <ItemStatusBadge status={item.status} />
                </dd>
              </div>
            </dl>
          </Card>

          <Card>
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold text-gray-900">Recovery Information</h2>
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-100 text-green-700">Public</span>
              </div>
              <button
                onClick={() => setShowRewardEdit(!showRewardEdit)}
                className="text-sm text-indigo-600 hover:text-indigo-800"
              >
                {showRewardEdit ? 'Cancel' : 'Edit Reward'}
              </button>
            </div>
            <dl className="space-y-4">
              <div>
                <dt className="text-sm font-medium text-gray-500 flex items-center gap-2">
                  Recovery Note
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-100 text-green-700">Public</span>
                </dt>
                <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                  {item.recovery_note || 'No recovery instructions provided'}
                </dd>
              </div>
            </dl>
          </Card>

          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Reward Settings</h2>
            
            {!showRewardEdit ? (
              <dl className="space-y-4">
                <div className="flex items-center justify-between">
                  <dt className="text-sm font-medium text-gray-500">Reward Enabled</dt>
                  <dd className="mt-1">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      rewardSettings?.reward_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {rewardSettings?.reward_enabled ? 'Yes' : 'No'}
                    </span>
                  </dd>
                </div>
                {rewardSettings?.reward_enabled && (
                  <>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Reward Amount</dt>
                      <dd className="mt-1 text-sm text-gray-900">
                        {rewardSettings.reward_amount_text || '-'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Reward Note</dt>
                      <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                        {rewardSettings.reward_note || '-'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Visibility</dt>
                      <dd className="mt-1 text-sm text-gray-900">
                        {rewardSettings?.reward_visibility === 'Public' ? 'Public (shown to finders)' : 
                         rewardSettings?.reward_visibility === 'Private Mention On Contact' ? 'Private (mention on contact)' : 
                         'Disabled'}
                      </dd>
                      <dd className="mt-1">
                        <RewardVisibilityBadge
                          visibility={rewardSettings?.reward_visibility || 'Public'}
                          hasReward={rewardSettings?.reward_enabled || false}
                          size="sm"
                        />
                      </dd>
                    </div>
                  </>
                )}
              </dl>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="rewardEnabled"
                    checked={rewardEnabled}
                    onChange={(e) => setRewardEnabled(e.target.checked)}
                    className="h-4 w-4 text-indigo-600 border-gray-300 rounded"
                  />
                  <label htmlFor="rewardEnabled" className="ml-2 block text-sm text-gray-900">
                    Enable reward for this item
                  </label>
                </div>
                
                {rewardEnabled && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Reward Amount</label>
                      <input
                        type="text"
                        value={rewardAmountText}
                        onChange={(e) => setRewardAmountText(e.target.value)}
                        placeholder="e.g., ₹500, $50"
                        className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Reward Note</label>
                      <textarea
                        value={rewardNote}
                        onChange={(e) => setRewardNote(e.target.value)}
                        placeholder="Any additional notes about the reward..."
                        rows={3}
                        className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Visibility</label>
                      <select
                        value={rewardVisibility}
                        onChange={(e) => setRewardVisibility(e.target.value)}
                        className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      >
                        <option value="Public">Public - Show to all finders</option>
                        <option value="Private Mention On Contact">Private - mention when contacted</option>
                      </select>
                      <p className="mt-1 text-xs text-gray-500">
                        Public: Reward details shown on scan page. Private: Only mentioned when finder contacts you.
                      </p>
                      <div className="mt-3 p-3 bg-blue-50 rounded-md">
                        <p className="text-xs text-blue-700">
                          <span className="font-medium">Public:</span> Shown to anyone who scans the QR code.
                          {' '}<span className="font-medium">Private:</span> Only revealed when the finder contacts you and you choose to share.
                        </p>
                      </div>
                    </div>
                  </>
                )}
                
                <div className="flex justify-end gap-2">
                  <button
                    onClick={handleCancelRewardEdit}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveReward}
                    disabled={isSavingReward || (rewardEnabled && !rewardAmountText)}
                    className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {isSavingReward ? 'Saving...' : 'Save Reward Settings'}
                  </button>
                </div>
              </div>
            )}
          </Card>

          {item.photos && item.photos.length > 0 && (
            <Card>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Photos</h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {item.photos.map((photo, idx) => (
                  <div key={idx} className="relative aspect-square bg-gray-100 rounded-lg overflow-hidden">
                    {photo.image ? (
                      <img 
                        src={photo.image} 
                        alt={photo.caption || 'Item photo'} 
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full text-gray-400">
                        No image
                      </div>
                    )}
                    {photo.caption && (
                      <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs p-1">
                        {photo.caption}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        <div className="space-y-6">
           <Card>
             <div className="flex items-start gap-3 mb-4">
               <div className="flex-shrink-0 h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center">
                 <svg className="h-5 w-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                 </svg>
               </div>
               <div>
                 <h3 className="text-base font-semibold text-gray-900">Privacy &amp; Visibility</h3>
                 <p className="text-sm text-gray-500 mt-0.5">What finders can see and what happens when they contact you</p>
               </div>
             </div>
             <div className="space-y-4">
               <div className="flex items-center justify-between">
                 <span className="text-sm text-gray-600">Public Label</span>
                 <PrivacyBadge visibility="Public" size="sm" />
               </div>
               <div className="flex items-center justify-between">
                 <span className="text-sm text-gray-600">Recovery Instructions</span>
                 <PrivacyBadge visibility="Public" size="sm" />
               </div>
               <div className="flex items-center justify-between">
                 <span className="text-sm text-gray-600">Reward Details</span>
                 <RewardVisibilityBadge
                   visibility={rewardSettings?.reward_visibility || 'Public'}
                   hasReward={rewardSettings?.reward_enabled || false}
                   size="sm"
                 />
               </div>
               <div className="flex items-center justify-between">
                 <span className="text-sm text-gray-600">Your Contact Info</span>
                 <PrivacyBadge visibility="Private" size="sm" />
               </div>
               <div className="border-t border-gray-100 pt-3">
                 <div className="space-y-2">
                   <p className="text-xs text-gray-500 leading-relaxed">
                     <span className="font-medium text-gray-600">Private:</span> Your name, email, phone, and address are never shown to finders.
                   </p>
                   <p className="text-xs text-gray-500 leading-relaxed">
                     <span className="font-medium text-gray-600">When contacted:</span> You receive a secure notification. You can reply without sharing your contact details unless you choose to include them in your message.
                   </p>
                   <p className="text-xs text-gray-500 leading-relaxed">
                     <span className="font-medium text-gray-600">Location sharing:</span> If you choose to share location, finders see your approximate location (not your exact address).
                   </p>
                 </div>
               </div>
             </div>
           </Card>

          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">QR Code</h2>
            {item.qr_code && (
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm font-medium text-gray-500">QR UID</dt>
                  <dd className="mt-1 text-sm font-mono text-gray-900">{item.qr_code.uid}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Status</dt>
                  <dd className="mt-1">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                      {item.qr_code.status}
                    </span>
                  </dd>
                </div>
              </dl>
            )}
          </Card>

          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Activity</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">Activated</dt>
                <dd className="mt-1 text-sm text-gray-900">{formatDate(item.activation_date)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Last Scan</dt>
                <dd className="mt-1 text-sm text-gray-900">{formatDate(item.last_scan_at)}</dd>
              </div>
            </dl>
          </Card>

          <Card padding="sm">
            <div className="flex items-start gap-3">
              <svg className="flex-shrink-0 h-5 w-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <div>
                <p className="text-sm text-blue-700">
                  Finders can scan the QR code to see your recovery notes and contact you. Your private contact details are never exposed.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </AppLayout>
  )
}

export default ItemDetail
