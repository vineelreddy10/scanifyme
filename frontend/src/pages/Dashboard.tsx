import { useAuth } from '../contexts/AuthContext'

const Dashboard = () => {
  const { currentUser, logout } = useAuth()

  const handleLogout = async () => {
    await logout()
    window.location.href = '/login'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">ScanifyMe</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                {currentUser as string}
              </span>
              <a
                href="/app/settings/users"
                className="text-sm text-indigo-600 hover:text-indigo-800"
              >
                Profile
              </a>
              <button
                onClick={handleLogout}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <h3 className="text-lg font-medium text-gray-900">Total Items</h3>
                <p className="mt-2 text-3xl font-bold text-indigo-600">0</p>
              </div>
            </div>
            
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <h3 className="text-lg font-medium text-gray-900">Active QR Codes</h3>
                <p className="mt-2 text-3xl font-bold text-green-600">0</p>
              </div>
            </div>
            
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <h3 className="text-lg font-medium text-gray-900">Recoveries</h3>
                <p className="mt-2 text-3xl font-bold text-blue-600">0</p>
              </div>
            </div>
          </div>

          <div className="mt-8 bg-white shadow rounded-lg">
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Welcome to ScanifyMe
              </h2>
              <p className="text-gray-600">
                Your QR-based item recovery platform. Start by adding items and 
                generating QR codes to attach to your belongings.
              </p>
              <div className="mt-4">
                <button className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">
                  Add Your First Item
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default Dashboard
