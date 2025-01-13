import dayjs from 'dayjs';
export declare const createOnChangeHandler: (path: string, handleChange: (path: string, value: any) => void, saveFormat: string | undefined) => (time: dayjs.Dayjs) => void;
export declare const getData: (data: any, saveFormat: string | undefined) => dayjs.Dayjs | null;
