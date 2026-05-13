import { useEffect } from 'react';
import { useLocation } from '@docusaurus/router';
import { useAnalytics } from '../AnalyticsProvider';

const useRouteAnalytics = () => {
  const location = useLocation();
  const { trackEvent } = useAnalytics();

  useEffect(() => {
    trackEvent("page_view", { 
      page_path: location.pathname,
      page_title: document.title
    });
  }, [location.pathname, trackEvent]);
};

export default useRouteAnalytics;
